"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, AlertTriangle } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { Button } from "@/components/ui/button"

const WS_BASE_URL = "ws://localhost:8080"

export function Page4() {
  const { toast } = useToast()
  const [logs, setLogs] = useState<string[]>([])
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting")
  const socketRef = useRef<WebSocket | null>(null)
  const logContainerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [])

  useEffect(() => {
    // Auto-scroll to the bottom when new logs arrive
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs])

  const connectWebSocket = () => {
    setStatus("connecting")
    
    const wsUrl = `${WS_BASE_URL}/api/logs`
    const socket = new WebSocket(wsUrl)
    socketRef.current = socket

    socket.onopen = () => {
      setStatus("connected")
      toast({
        title: "Connected to logs stream",
        description: "You are now receiving live logs",
      })
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.log) {
          setLogs(prevLogs => [...prevLogs, data.log])
        }
      } catch (error) {
        console.error("Invalid message format:", error)
      }
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", error)
      setStatus("disconnected")
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: "Failed to connect to logs stream",
      })
    }

    socket.onclose = () => {
      setStatus("disconnected")
    }
  }

  const reconnect = () => {
    if (socketRef.current) {
      socketRef.current.close()
    }
    setLogs([])
    connectWebSocket()
  }

  const clearLogs = () => {
    setLogs([])
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Live Logs</h2>
        <div className="flex items-center gap-2">
          {status === "connected" ? (
            <span className="flex items-center text-sm text-green-500">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-green-500"></span>
              Connected
            </span>
          ) : status === "connecting" ? (
            <span className="flex items-center text-sm text-yellow-500">
              <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
              Connecting...
            </span>
          ) : (
            <span className="flex items-center text-sm text-red-500">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-red-500"></span>
              Disconnected
            </span>
          )}
          <Button variant="outline" size="sm" onClick={reconnect}>
            Reconnect
          </Button>
          <Button variant="outline" size="sm" onClick={clearLogs}>
            Clear
          </Button>
        </div>
      </div>

      <Card className="h-[calc(100vh-12rem)]">
        <CardContent className="p-0">
          {status === "connecting" && logs.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : status === "disconnected" && logs.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
              <AlertTriangle className="h-8 w-8" />
              <p>Connection lost. Please reconnect.</p>
              <Button variant="outline" size="sm" onClick={reconnect}>
                Reconnect
              </Button>
            </div>
          ) : (
            <div 
              ref={logContainerRef}
              className="h-full max-h-[calc(100vh-12rem)] overflow-auto p-4 font-mono text-sm"
            >
              {logs.length === 0 ? (
                <p className="text-center text-muted-foreground">No logs received yet</p>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="border-b border-border py-1 last:border-0">
                    {log}
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}