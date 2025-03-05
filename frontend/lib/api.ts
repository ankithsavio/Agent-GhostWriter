// API utility functions for making requests to the FastAPI backend
const API_BASE_URL = "http://localhost:8080"
const WS_BASE_URL = "ws://localhost:8080"

export async function uploadFile(file: File, docNumber: 1 | 2) {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("docNumber", docNumber.toString())

  const response = await fetch(`${API_BASE_URL}/api/upload_document`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`)
  }

  return response.json()
}

export async function uploadText(text: string) {
  const response = await fetch(`${API_BASE_URL}/api/upload_text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw new Error(`Text upload failed: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchConversations() {
  const response = await fetch(`${API_BASE_URL}/conversations`, {
    method: "GET",
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchAvailableFunctions() {
  const response = await fetch(`${API_BASE_URL}/api/available_functions`, {
    method: "GET",
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch functions: ${response.statusText}`)
  }

  return response.json()
}

export async function applyFunction(functionName: string, docNumber: 1 | 2) {
  const response = await fetch(`${API_BASE_URL}/api/apply_function`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ functionName, docNumber }),
  })

  if (!response.ok) {
    throw new Error(`Function application failed: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchDocument(docNumber: 1 | 2) {
  const response = await fetch(`${API_BASE_URL}/api/document/${docNumber}`, {
    method: "GET",
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch document: ${response.statusText}`)
  }

  return response.json()
}

export function createDocumentWebSocket(number: number) {
  return new WebSocket(`${WS_BASE_URL}/api/document/${number}`)
}

export function createConversationWebSocket(personaName: string) {
  return new WebSocket(`${WS_BASE_URL}/ws/conversation/${personaName}`)
}

export async function fetchResearchDocument() {
  const response = await fetch(`${API_BASE_URL}/research_doc`, {
    method: "GET",
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch research document: ${response.statusText}`)
  }

  return response.json()
}

export async function uploadDocuments(doc1: File, doc2: File) {
  const formData = new FormData()
  formData.append("doc1", doc1)
  formData.append("doc2", doc2)

  const response = await fetch(`${API_BASE_URL}/api/upload_documents`, {
    method: "POST",
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`)
  }

  return response.json()
}

