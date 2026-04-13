import React, { useRef, useState, useEffect } from 'react'
import { Button, Space, Upload, message } from 'antd'
import { UploadOutlined, ClearOutlined, CheckOutlined } from '@ant-design/icons'

interface SignaturePadProps {
  onSave: (base64Image: string) => void
  width?: number
  height?: number
}

const SignaturePad: React.FC<SignaturePadProps> = ({ onSave, width, height = 200 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [hasDrawing, setHasDrawing] = useState(false)

  const initCanvas = (canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.strokeStyle = '#000000'
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    if (width) {
      canvas.width = width
      canvas.height = height
      initCanvas(canvas)
      return
    }
    const el = wrapperRef.current
    if (!el) return
    const resize = () => {
      const w = Math.max(el.clientWidth, 300)
      if (canvas.width !== w || canvas.height !== height) {
        canvas.width = w
        canvas.height = height
        initCanvas(canvas)
      }
    }
    resize()
    let ro: ResizeObserver | null = null
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(resize)
      ro.observe(el)
    } else {
      window.addEventListener('resize', resize)
    }
    return () => {
      if (ro) {
        ro.disconnect()
      } else {
        window.removeEventListener('resize', resize)
      }
    }
  }, [width, height])

  const getPos = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    const rect = canvas.getBoundingClientRect()
    if ('touches' in e) {
      return {
        x: e.touches[0].clientX - rect.left,
        y: e.touches[0].clientY - rect.top,
      }
    }
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    }
  }

  const startDraw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    setIsDrawing(true)
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const { x, y } = getPos(e)
    ctx.beginPath()
    ctx.moveTo(x, y)
  }

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    if (!isDrawing) return
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const { x, y } = getPos(e)
    ctx.lineTo(x, y)
    ctx.stroke()
    setHasDrawing(true)
  }

  const endDraw = () => {
    setIsDrawing(false)
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    ctx.closePath()
  }

  const clear = () => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    setHasDrawing(false)
  }

  const save = () => {
    const canvas = canvasRef.current
    if (!canvas || !hasDrawing) {
      message.warning('请先签名')
      return
    }
    const base64 = canvas.toDataURL('image/png')
    onSave(base64)
  }

  const handleUpload = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const result = e.target?.result as string
      if (result) {
        onSave(result)
      }
    }
    reader.readAsDataURL(file)
    return false
  }

  return (
    <div ref={wrapperRef}>
      <canvas
        ref={canvasRef}
        width={width || 400}
        height={height}
        style={{ border: '1px solid #d9d9d9', borderRadius: 4, cursor: 'crosshair', display: 'block', maxWidth: '100%' }}
        onMouseDown={startDraw}
        onMouseMove={draw}
        onMouseUp={endDraw}
        onMouseLeave={endDraw}
        onTouchStart={startDraw}
        onTouchMove={draw}
        onTouchEnd={endDraw}
      />
      <Space style={{ marginTop: 12 }}>
        <Button icon={<ClearOutlined />} onClick={clear}>清空</Button>
        <Button type="primary" icon={<CheckOutlined />} onClick={save} disabled={!hasDrawing}>确认签名</Button>
        <Upload beforeUpload={handleUpload} showUploadList={false} accept="image/png,image/jpeg">
          <Button icon={<UploadOutlined />}>上传签名图片</Button>
        </Upload>
      </Space>
    </div>
  )
}

export default SignaturePad
