export async function downloadExport(url: string, filename: string) {
  const res = await fetch(url, { credentials: 'include' })
  if (!res.ok) {
    const err = await res.text().catch(() => '导出失败')
    throw new Error(err)
  }
  const blob = await res.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = downloadUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(downloadUrl)
}
