export type Regel = {
  regel: string
  status: string
  ausfuehrbar: boolean
  hinweis: string
  owner: string
  version: number
  grenzfaelle: string
  festigkeit: string
  offene_fragen: string
}

declare module 'claude-code' {
  interface PluginState {
    'regel-cockpit': { regeln: Shaped<Regel[]> }
  }
}
