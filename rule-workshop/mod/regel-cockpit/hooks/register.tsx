import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Regel } from '../types'

// Regel-Cockpit: gilt nur in Ordnern, die eine Regelwerkstatt enthalten.
const PANE = 'regel-cockpit'
const ENGINE = 'engine/regelwerk.py'
// Direkter Weg zu den Daten, vorbei an freigegebenen Regeln.
const DIREKT = /\b(sqlite3|psql|pg_dump|duckdb)\b|\.sqlite\b/i
const FREMDES_SQL = /^mcp__(?!regelwerk__).+__(query|execute_sql|run_sql|sql)$/
const SPERRE =
  'Regelwerkstatt: Direkter Datenzugriff ist hier gesperrt. Daten gibt es nur über freigegebene Regeln (regel_liste, regel_ausfuehren).'
const ZEICHEN: Record<string, string> = { certified: '✅', review: '🟡', draft: '✏️', suspended: '⛔' }

const regeln = atom({ plugin: 'regel-cockpit', key: 'regeln' } as const, [], { shape: 'regeln-1' })

let istWerkstatt: boolean | undefined

async function werkstatt($: EngineInterface): Promise<boolean> {
  if (istWerkstatt === undefined) {
    try {
      istWerkstatt = (await $.process.run(['test', '-f', ENGINE])).exitCode === 0
    } catch {
      istWerkstatt = false
    }
  }
  return istWerkstatt
}

async function lade($: EngineInterface): Promise<void> {
  try {
    const lauf = await $.process.run(['python3', ENGINE, 'liste'], { timeoutMs: 20000 })
    if (lauf.exitCode !== 0) return
    const liste = JSON.parse(lauf.stdout) as Regel[]
    await update($, regeln, () => liste)
  } catch {
    // Das Cockpit ist Anzeige: ein Fehler hier darf die Arbeit nicht aufhalten.
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    if (await werkstatt($)) {
      await $.command.register({ name: 'regel-cockpit', description: 'Stand aller Regeln der Regelwerkstatt anzeigen' })
      await lade($)
      void $.ui.open({ id: PANE, title: 'Regel-Cockpit' })
    }
    return started
  })

  on('command.run', { command: 'regel-cockpit' }, async $ => {
    await lade($)
    await $.ui.open({ id: PANE, title: 'Regel-Cockpit' })
    return { text: 'Regel-Cockpit geöffnet.' }
  })

  on('tool.call', async ($, e, next) => {
    if (!(await werkstatt($))) return next(e)
    if (e.tool === 'Bash' && DIREKT.test(e.command) && !e.command.includes(ENGINE)) return { deny: SPERRE }
    if (FREMDES_SQL.test(e.tool)) return { deny: SPERRE }
    const ran = await next(e)
    const beruehrtRegeln =
      e.tool.startsWith('mcp__regelwerk__') ||
      (e.tool === 'Bash' && e.command.includes(ENGINE)) ||
      ((e.tool === 'Edit' || e.tool === 'Write') && e.file_path.includes('/Regeln/'))
    if (beruehrtRegeln) await lade($)
    return ran
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const liste = await read($, regeln)
    return (
      <Box flexDirection="column">
        {liste.length === 0 && <Text dimColor>Noch keine Regeln gefunden.</Text>}
        {liste.map(r => (
          <Box flexDirection="column">
            <Text>
              {ZEICHEN[r.status] ?? '•'} {r.regel} {r.version > 0 ? `v${r.version}` : ''}
            </Text>
            <Text dimColor>
              {'   '}
              {r.owner || 'kein Owner'} · Grenzfälle {r.grenzfaelle || '–'} · Festigkeit {r.festigkeit || '–'} % · offene Fragen{' '}
              {r.offene_fragen || '0'}
            </Text>
            {!r.ausfuehrbar && <Text dimColor>{'   '}nicht ausführbar: {r.hinweis}</Text>}
          </Box>
        ))}
      </Box>
    )
  })
}
