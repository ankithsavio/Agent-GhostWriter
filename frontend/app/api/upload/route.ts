import { NextResponse } from "next/server"

export async function POST(req: Request) {
  try {
    const formData = await req.formData()
    const file = formData.get("file") as File
    const docType = formData.get("docType") as string

    // Here you would typically process the file on the backend
    // For example, extracting text, storing it, etc.

    // Simulating backend processing
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const processedContent = `Processed content of ${file.name} (${docType})`

    return NextResponse.json({
      success: true,
      filename: file.name,
      docType,
      processedContent,
    })
  } catch (error) {
    return NextResponse.json({ error: "Failed to process file" }, { status: 500 })
  }
}

