import { useEffect, useState } from 'react'

import type { ConnectorHealth, ConstellationConnector } from './constellationModel'

const API = 'http://127.0.0.1:8000'

export type ConnectorHealthCheck = {
  state: ConnectorHealth
  checkedAt?: string
}

export function useConnectorHealth(connectors: readonly ConstellationConnector[]) {
  const [checks, setChecks] = useState<Record<string, ConnectorHealthCheck>>({})

  useEffect(() => {
    const controller = new AbortController()

    void Promise.all(connectors.map(async (connector) => {
      if (!connector.healthEndpoint) return [connector.id, { state: 'unknown' }] as const

      try {
        const response = await fetch(`${API}${connector.healthEndpoint}`, { signal: controller.signal })
        const payload = await response.json().catch(() => ({})) as { ok?: boolean }
        const state: ConnectorHealth = response.ok && payload.ok !== false
          ? 'healthy'
          : response.status < 500
            ? 'degraded'
            : 'down'
        return [connector.id, { state, checkedAt: new Date().toISOString() }] as const
      } catch {
        return [connector.id, { state: 'unknown', checkedAt: new Date().toISOString() }] as const
      }
    })).then((entries) => {
      if (!controller.signal.aborted) setChecks(Object.fromEntries(entries))
    })

    return () => controller.abort()
  }, [connectors])

  return checks
}
