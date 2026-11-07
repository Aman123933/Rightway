import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import EmergencyModal from './components/EmergencyModal'
import Home from './pages/Home'
import Answer from './pages/Answer'
import Draft from './pages/Draft'
import Sources from './pages/Sources'
import About from './pages/About'

export default function App() {
  const [emergencyOpen, setEmergencyOpen] = useState(false)

  const handleOpenEmergency = () => setEmergencyOpen(true)
  const handleCloseEmergency = () => setEmergencyOpen(false)

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar onOpenEmergency={handleOpenEmergency} />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home onOpenEmergency={handleOpenEmergency} />} />
          <Route path="/answer" element={<Answer onOpenEmergency={handleOpenEmergency} />} />
          <Route path="/draft" element={<Draft />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>

      <Footer />

      <EmergencyModal isOpen={emergencyOpen} onClose={handleCloseEmergency} />
    </div>
  )
}
