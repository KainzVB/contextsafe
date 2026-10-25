-- =============================================================================
-- TPC-H Query 3: Top 10 Shipping Priorities by Revenue
-- =============================================================================
-- Segment:   BUILDING
-- Stichtag:  1995-03-15
-- Limit:     10
-- Schema:    tpch_customer, tpch_orders, tpch_lineitems
-- Hinweis:   Datumsspalten sind varchar -> expliziter CAST AS DATE
-- =============================================================================

SELECT
    o_orderkey,
    SUM(l_extendedprice * (1 - l_discount)) AS revenue,
    o_orderdate,
    o_shippriority
FROM
    tpch_customer
    INNER JOIN tpch_orders ON c_custkey = o_custkey
    INNER JOIN tpch_lineitems ON o_orderkey = l_orderkey
WHERE
    c_mktsegment = 'BUILDING'
    AND CAST(o_orderdate AS DATE) < DATE '1995-03-15'
    AND CAST(l_shipdate AS DATE) > DATE '1995-03-15'
GROUP BY
    o_orderkey,
    o_orderdate,
    o_shippriority
ORDER BY
    revenue DESC,
    o_orderdate ASC
LIMIT 10;
