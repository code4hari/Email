import React from 'react';
import { Mail } from 'lucide-react';
import './EmailToolAd.css';

const EmailToolAd = () => {
  const generateIcon = (index) => {
    const speed = 4 + Math.random() * 2; // Speed between 4 and 6 seconds
    const lane = Math.floor(Math.random() * 5); // 5 lanes
    const delay = Math.random() * 5; // Random start time
    const yOffset = Math.random() * 40 - 20; // Random vertical offset
    
    // Two fixed nodes
    const nodeY = Math.random() < 0.5 ? -30 : 30;
    
    // Final positions branching out from the nodes
    const finalY = nodeY + (Math.random() - 0.5) * 40;

    return (
      <Mail 
        key={index}
        className="absolute text-gray-600 animate-slide"
        style={{
          top: `${20 + lane * 15}%`,
          left: `-50px`,
          animationDuration: `${speed}s`,
          animationDelay: `${delay}s`,
          opacity: 0.6 + Math.random() * 0.4,
          fontSize: `${14 + Math.random() * 10}px`,
          '--y-offset': yOffset,
          '--node-y': nodeY,
          '--final-y': finalY,
        }}
      />
    );
  };

  return (
    <div className="bg-black text-white relative w-full h-48 flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0">
        {[...Array(60)].map((_, index) => generateIcon(index))}
      </div>
      <div className="text-center z-10 bg-black bg-opacity-70 p-4 rounded">
        <Mail className="w-8 h-8 text-white mb-2 mx-auto" />
        <h1 className="text-2xl font-bold mb-2">Stop wasting time on email.</h1>
        <p className="text-sm max-w-md mx-auto mb-4">
          Revamp your life today. Be prepared to inbox-zero like you've never inbox-zeroed before.
        </p>
        <button className="bg-white text-black py-2 px-4 rounded-full font-semibold text-sm">
          Get Started &gt;
        </button>
      </div>
    </div>
  );
};

export default EmailToolAd;