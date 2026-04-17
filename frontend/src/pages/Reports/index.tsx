import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ReportList from './ReportList'
import ReportViewer from './ReportViewer'

const Reports: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<ReportList />} />
      <Route path="/:reportId" element={<ReportViewer />} />
      <Route path="*" element={<Navigate to="/reports" replace />} />
    </Routes>
  )
}

export default Reports
