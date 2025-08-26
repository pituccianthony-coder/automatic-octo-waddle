// frontend/src/components/GlitchArt.js
'use client'; // Это — заклинание, чтобы Next.js понял, что здесь будет магия на стороне клиента.

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Torus, EffectComposer, Glitch, Bloom } from '@react-three/drei';
import { GlitchMode } from 'postprocessing';

function RotatingTorus() {
  // Этот реф — наша прямая связь с объектом в 3D-пространстве.
  const meshRef = useRef();

  // useFrame — это хук, который выполняется на каждом кадре.
  // Заставляем наш торус вечно вращаться, как сансара.
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.2;
      meshRef.current.rotation.y += delta * 0.1;
    }
  });

  return (
    <Torus ref={meshRef} args={[1, 0.4, 32, 100]}>
      <meshStandardMaterial color="cyan" wireframe />
    </Torus>
  );
}

/**
 * Главный компонент, который рендерит 3D-сцену и применяет к ней эффекты.
 * @param {object} gene - "Ген", полученный от API, управляющий эффектами.
 */
export default function GlitchArt({ gene }) {
  // // Здесь мы будем управлять реальностью на основе гена.
  // // Пока что используем заглушки, но скоро... о, скоро здесь будет хаос.
  const isGlitching = gene ? gene.rhythm > 0.7 : false;
  const aggression = gene ? gene.aggression : 0;
  const complexity = gene ? gene.complexity : 0;

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000' }}>
      <Canvas>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <RotatingTorus />

        {/* Компоновщик эффектов. Это наш холст для пост-обработки. */}
        <EffectComposer>
          {/* Эффект свечения. Сложность поэмы будет влиять на его интенсивность. */}
          <Bloom
            intensity={0.5 + complexity * 2.0} // от 0.5 до 2.5
            luminanceThreshold={0}
            luminanceSmoothing={0.9}
            height={300}
          />
          {/* Эффект глитча. Агрессия поэмы будет делать его сильнее. */}
          <Glitch
            delay={[0.5, 1.5]} // min/max glitch delay
            duration={[0.1, 0.3]} // min/max glitch duration
            strength={[0.01 * aggression, 0.2 * aggression]} // min/max glitch strength
            mode={GlitchMode.SPORADIC}
            active={isGlitching} // Ритм решает, будет ли глитч вообще.
          />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
