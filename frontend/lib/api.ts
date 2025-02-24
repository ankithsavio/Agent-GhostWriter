import { io, type Socket } from "socket.io-client"

const API_BASE_URL = "http://localhost:8000"
let socket: Socket

export function initializeSocket() {
  socket = io(API_BASE_URL)
  return socket
}

export async function uploadFile(file: File, docType: string) {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("docType", docType)

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new Error("Upload failed")
  }

  return response.json()
}

export async function processText(text: string) {
  const response = await fetch(`${API_BASE_URL}/process-text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw new Error("Processing failed")
  }

  return response.json()
}

export async function getProgressStages() {
  const response = await fetch(`${API_BASE_URL}/progress-stages`)

  if (!response.ok) {
    throw new Error("Failed to fetch progress stages")
  }

  return response.json()
}

export async function getAvailableFunctions() {
  const response = await fetch(`${API_BASE_URL}/available-functions`)

  if (!response.ok) {
    throw new Error("Failed to fetch available functions")
  }

  return response.json()
}

export async function getDocumentContent(docType: string) {
  const response = await fetch(`${API_BASE_URL}/document-content/${docType}`)

  if (!response.ok) {
    throw new Error("Failed to fetch document content")
  }

  return response.json()
}

export async function applyFunction(functionName: string, content: string, docType: string) {
  const response = await fetch(`${API_BASE_URL}/apply-function/${functionName}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content, docType }),
  })

  if (!response.ok) {
    throw new Error("Function application failed")
  }

  return response.json()
}

