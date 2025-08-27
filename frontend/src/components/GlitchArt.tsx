'use client';

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Torus, EffectComposer, Glitch, Bloom } from '@react-three/drei';
import { GlitchMode } from 'postprocessing';

function RotatingTorus() {
  const meshRef = useRef<any>();

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

export default function GlitchArt({ gene }: { gene: any }) {
  const isGlitching = gene ? gene.rhythm > 0.7 : false;
  const aggression = gene ? gene.aggression : 0;
  const complexity = gene ? gene.complexity : 0;

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000' }}>
      <Canvas>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <RotatingTorus />

        <EffectComposer>
          <Bloom
            intensity={0.5 + complexity * 2.0}
            luminanceThreshold={0}
            luminanceSmoothing={0.9}
            height={300}
          />
          <Glitch
            delay={[0.5, 1.5]}
            duration={[0.1, 0.3]}
            strength={[0.01 * aggression, 0.2 * aggression]}
            mode={GlitchMode.SPORADIC}
            active={isGlitching}
          />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
