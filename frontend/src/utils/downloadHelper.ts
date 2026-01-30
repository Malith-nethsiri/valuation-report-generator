/**
 * File download utilities for handling blob downloads with proper filename extraction.
 * Consolidates duplicate download logic from api.ts and useJobPolling.ts.
 */

/**
 * Extract filename from Content-Disposition header.
 *
 * @param contentDisposition - The Content-Disposition header value from response
 * @param defaultName - Default filename if extraction fails
 * @returns The extracted filename or default
 *
 * @example
 * extractFilenameFromHeader('attachment; filename="report.docx"') // "report.docx"
 * extractFilenameFromHeader('attachment; filename=document.pdf') // "document.pdf"
 * extractFilenameFromHeader(null) // "document.docx"
 */
export function extractFilenameFromHeader(
  contentDisposition: string | null | undefined,
  defaultName: string = 'document.docx'
): string {
  if (!contentDisposition) return defaultName;

  // Try to match filename with or without quotes
  const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
  return filenameMatch ? filenameMatch[1] : defaultName;
}

/**
 * Trigger a file download from blob data.
 * Creates a temporary URL, clicks a hidden link, and cleans up.
 *
 * @param blobData - The blob data to download
 * @param filename - The filename for the downloaded file
 *
 * @example
 * const blob = new Blob([response.data], { type: 'application/pdf' });
 * downloadBlobFile(blob, 'report.pdf');
 */
export function downloadBlobFile(
  blobData: Blob,
  filename: string
): void {
  const url = window.URL.createObjectURL(blobData);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * MIME type for Word documents (DOCX format).
 */
export const DOCX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

/**
 * Create a properly typed blob for DOCX files from response data.
 *
 * @param data - The raw response data
 * @returns Blob with correct MIME type for DOCX
 */
export function createDocxBlob(data: BlobPart): Blob {
  return new Blob([data], { type: DOCX_MIME_TYPE });
}

/**
 * Combined utility: Extract filename from headers and trigger download.
 * Convenience function for common download pattern.
 *
 * @param responseData - Raw response data to download
 * @param contentDisposition - Content-Disposition header value
 * @param defaultFilename - Fallback filename
 * @param mimeType - MIME type for the blob (defaults to DOCX)
 */
export function downloadFromResponse(
  responseData: BlobPart,
  contentDisposition: string | null | undefined,
  defaultFilename: string = 'document.docx',
  mimeType: string = DOCX_MIME_TYPE
): void {
  const filename = extractFilenameFromHeader(contentDisposition, defaultFilename);
  const blob = new Blob([responseData], { type: mimeType });
  downloadBlobFile(blob, filename);
}
