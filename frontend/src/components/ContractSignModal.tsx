import React, { useState, useEffect } from 'react'
import { Modal, Steps, Button, message, Input, Space, Tabs } from 'antd'
import { EyeOutlined, RedoOutlined } from '@ant-design/icons'
import SignaturePad from './SignaturePad'
import { useSignContractMutation, useUploadSignedContractMutation, contractsApi } from '@/store/api/contractsApi'

interface ContractSignModalProps {
  contractId: number
  open: boolean
  onClose: () => void
  onOpenPdf?: (id: number) => void
  partyANameDefault?: string
  partyBNameDefault?: string
}

const ContractSignModal: React.FC<ContractSignModalProps> = ({
  contractId,
  open,
  onClose,
  onOpenPdf,
  partyANameDefault,
  partyBNameDefault,
}) => {
  const [activeTab, setActiveTab] = useState<'online' | 'upload'>('online')

  // Online sign state
  const [currentStep, setCurrentStep] = useState(0)
  const [partyAName, setPartyAName] = useState('')
  const [partyASignature, setPartyASignature] = useState('')
  const [partyAPreview, setPartyAPreview] = useState('')
  const [partyBName, setPartyBName] = useState('')
  const [partyBSignature, setPartyBSignature] = useState('')
  const [partyBPreview, setPartyBPreview] = useState('')

  // Upload sign state
  const [fileUrl, setFileUrl] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [signContract] = useSignContractMutation()
  const [uploadSignedContract] = useUploadSignedContractMutation()
  const [triggerDraftUrl, { isFetching: draftUrlLoading }] = contractsApi.useLazyGetContractDraftUrlQuery()

  useEffect(() => {
    if (open) {
      setPartyAName(partyANameDefault || '')
      setPartyBName(partyBNameDefault || '')
      setActiveTab('online')
      setCurrentStep(0)
      setPartyASignature('')
      setPartyAPreview('')
      setPartyBSignature('')
      setPartyBPreview('')
      setFileUrl('')
      setSubmitting(false)
    }
  }, [open, partyANameDefault, partyBNameDefault])

  const handleSaveA = (base64: string) => {
    setPartyASignature(base64)
    setPartyAPreview(base64)
    message.success('甲方签名已确认')
  }

  const handleSaveB = (base64: string) => {
    setPartyBSignature(base64)
    setPartyBPreview(base64)
    message.success('乙方签名已确认')
  }

  const handleNext = () => {
    if (!partyAName.trim()) {
      message.error('请输入甲方签署人姓名')
      return
    }
    if (!partyASignature) {
      message.error('请完成甲方签名')
      return
    }
    setCurrentStep(1)
  }

  const handleSubmitOnline = async () => {
    if (!partyBName.trim()) {
      message.error('请输入乙方签署人姓名')
      return
    }
    if (!partyBSignature) {
      message.error('请完成乙方签名')
      return
    }
    setSubmitting(true)
    try {
      await signContract({
        id: contractId,
        data: {
          party_a_name: partyAName,
          party_a_signature_base64: partyASignature,
          party_b_name: partyBName,
          party_b_signature_base64: partyBSignature,
        },
      }).unwrap()
      message.success('合同签订成功')
      handleClose()
      if (onOpenPdf) {
        onOpenPdf(contractId)
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '签订失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitUpload = async () => {
    if (!fileUrl.trim()) {
      message.error('请输入已盖章 PDF 的文件路径')
      return
    }
    setSubmitting(true)
    try {
      await uploadSignedContract({
        id: contractId,
        data: { file_url: fileUrl.trim() },
      }).unwrap()
      message.success('合同上传盖章版成功')
      handleClose()
      if (onOpenPdf) {
        onOpenPdf(contractId)
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '上传盖章版失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setCurrentStep(0)
    setPartyAName('')
    setPartyASignature('')
    setPartyAPreview('')
    setPartyBName('')
    setPartyBSignature('')
    setPartyBPreview('')
    setFileUrl('')
    setSubmitting(false)
    onClose()
  }

  const openDraftPreview = async () => {
    try {
      const res = await triggerDraftUrl(contractId).unwrap()
      if (res.url) {
        window.open(res.url, '_blank')
      } else {
        message.error('获取草稿预览链接失败')
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '预览失败')
    }
  }

  const tabItems = [
    {
      key: 'online',
      label: '在线双签',
      children: (
        <div>
          <Steps current={currentStep} size="small" style={{ marginBottom: 24 }}>
            <Steps.Step title="甲方签名" />
            <Steps.Step title="乙方签名" />
          </Steps>

          {currentStep === 0 && (
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Input
                  placeholder="甲方签署人姓名"
                  value={partyAName}
                  onChange={(e) => setPartyAName(e.target.value)}
                  maxLength={50}
                />
                {partyAPreview ? (
                  <div>
                    <img
                      src={partyAPreview}
                      alt="甲方签名"
                      style={{
                        maxWidth: '100%',
                        height: 120,
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        background: '#fff',
                      }}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Button icon={<RedoOutlined />} onClick={() => { setPartyAPreview(''); setPartyASignature('') }}>
                        重新签名
                      </Button>
                    </div>
                  </div>
                ) : (
                  <SignaturePad onSave={handleSaveA} height={200} />
                )}
              </Space>
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Button type="primary" onClick={handleNext}>下一步</Button>
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Input
                  placeholder="乙方签署人姓名"
                  value={partyBName}
                  onChange={(e) => setPartyBName(e.target.value)}
                  maxLength={50}
                />
                {partyBPreview ? (
                  <div>
                    <img
                      src={partyBPreview}
                      alt="乙方签名"
                      style={{
                        maxWidth: '100%',
                        height: 120,
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        background: '#fff',
                      }}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Button icon={<RedoOutlined />} onClick={() => { setPartyBPreview(''); setPartyBSignature('') }}>
                        重新签名
                      </Button>
                    </div>
                  </div>
                ) : (
                  <SignaturePad onSave={handleSaveB} height={200} />
                )}
              </Space>
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Space>
                  <Button disabled={submitting} onClick={() => setCurrentStep(0)}>上一步</Button>
                  <Button type="primary" loading={submitting} onClick={handleSubmitOnline}>
                    {submitting ? '正在生成PDF，请稍候...' : '提交签订'}
                  </Button>
                </Space>
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'upload',
      label: '上传盖章版',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ color: '#666', marginBottom: 8 }}>
            请先将合同打印、盖章并扫描为 PDF，然后将 PDF 上传至文件系统，再在此处填写文件路径。
          </div>
          <Input.TextArea
            placeholder="请输入已盖章 PDF 的 MinIO 文件路径，例如：contracts/123/finals/signed.pdf"
            value={fileUrl}
            onChange={(e) => setFileUrl(e.target.value)}
            rows={3}
          />
          <div style={{ textAlign: 'right', marginTop: 16 }}>
            <Button type="primary" loading={submitting} onClick={handleSubmitUpload}>
              确认已签订
            </Button>
          </div>
        </Space>
      ),
    },
  ]

  return (
    <Modal
      title="合同签订"
      open={open}
      onCancel={handleClose}
      width={640}
      footer={null}
      maskClosable={!submitting}
      closable={!submitting}
    >
      <div style={{ marginBottom: 16 }}>
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={openDraftPreview}
          loading={draftUrlLoading}
        >
          查看合同草稿
        </Button>
      </div>

      <Tabs activeKey={activeTab} onChange={(k) => setActiveTab(k as 'online' | 'upload')} items={tabItems} />
    </Modal>
  )
}

export default ContractSignModal
