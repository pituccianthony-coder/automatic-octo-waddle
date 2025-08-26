// frontend/src/app/page.tsx
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import GlitchArt from '@/components/GlitchArt';

// Массив текстов, которые мы будем поочередно скармливать поэту.
// Поэзия, проза, код... для нашего AI все это — просто данные.
const TEXT_SAMPLES = [
  `Tyger Tyger, burning bright,
   In the forests of the night;
   What immortal hand or eye,
   Could frame thy fearful symmetry?`,
  `The market is a device for transferring money from the impatient to the patient.`,
  `function life() { while(true) { try { learn(); grow(); } catch(e) { handle(e); } } }`,
  `Do not go gentle into that good night, Old age should burn and rave at close of day; Rage, rage against the dying of the light.`
];

export default function Home() {
  const [gene, setGene] = useState(null);
  const [currentText, setCurrentText] = useState(TEXT_SAMPLES[0]);
  const [error, setError] = useState('');

  useEffect(() => {
    // Эта функция будет вызывать наш API
    const fetchGene = async (text: string) => {
      try {
        const response = await axios.post('http://localhost:8000/generate_from_text', { text });
        setGene(response.data.gene_used);
        setError('');
      } catch (err) {
        console.error("Error fetching gene from backend:", err);
        setError('Failed to connect to the EchoVoid oracle. Is the backend running?');
      }
    };

    // Вызываем ее сразу при загрузке
    fetchGene(currentText);

    // А затем устанавливаем интервал, чтобы "мысли" бота постоянно менялись
    const intervalId = setInterval(() => {
      const nextText = TEXT_SAMPLES[Math.floor(Math.random() * TEXT_SAMPLES.length)];
      setCurrentText(nextText);
      fetchGene(nextText);
    }, 5000); // каждые 5 секунд

    // Очищаем интервал при размонтировании компонента
    return () => clearInterval(intervalId);
  }, []);

  return (
    <main style={{ position: 'relative' }}>
      <GlitchArt gene={gene} />
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        color: 'white',
        fontFamily: 'monospace',
        maxWidth: '50%',
        background: 'rgba(0,0,0,0.5)',
        padding: '10px',
        borderRadius: '5px'
      }}>
        <h1>EchoVoid</h1>
        <p>Status: {error ? <span style={{color: 'red'}}>{error}</span> : 'Connected. Observing the void.'}</p>
        <p>Current Inspiration:</p>
        <pre style={{ whiteSpace: 'pre-wrap', borderLeft: '2px solid cyan', paddingLeft: '10px' }}>
          <code>{currentText}</code>
        </pre>
        <p>Generated Gene:</p>
        <pre style={{ whiteSpace: 'pre-wrap' }}>
          <code>{JSON.stringify(gene, null, 2)}</code>
        </pre>
      </div>
    </main>
  );
}
