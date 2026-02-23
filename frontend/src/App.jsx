import React, { useEffect, useState } from 'react'

export default function App() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    fetch('http://127.0.0.1:8000')
      .then((r) => r.json())
      .then((data) => setMessage(data.hello || JSON.stringify(data)))
      .catch(() => setMessage('Could not reach backend'))
  }, [])

  return (
    <div style={{fontFamily: 'sans-serif', padding: 20}}>
      <h1>Vite + React</h1>
      <p>Backend says: {message}</p>
    </div>
  )
}

