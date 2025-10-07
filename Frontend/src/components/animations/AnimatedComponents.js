// ============ NEW FILE: components/animations/AnimatedComponents.js ============
// Import this in your modals to use these animated components

import React, { useState, useEffect } from 'react';
import { FolderOpen } from 'lucide-react';

// ============ ANIMATED LIST ITEM COMPONENT ============
export const AnimatedListItem = ({ children, delay = 0, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timeout);
  }, [delay]);

  return (
    <div
      className={`animate-list-item ${className}`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateX(0)' : 'translateX(-20px)',
        transition: 'all 0.5s ease',
      }}
    >
      {children}
    </div>
  );
};

// ============ ANIMATED FOLDER INPUT COMPONENT ============
export const AnimatedFolderInput = ({ 
  isOpen, 
  onToggle, 
  label = 'Upload Document',
  children,
  className = '' 
}) => {
  return (
    <div className={`folder-container ${className}`}>
      <button
        onClick={onToggle}
        className="folder-trigger"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '1rem 1.5rem',
          background: isOpen 
            ? 'linear-gradient(135deg, var(--accent-light), var(--bg-secondary))' 
            : 'var(--bg-secondary)',
          border: `2px solid ${isOpen ? 'var(--accent-primary)' : 'var(--border-color)'}`,
          borderRadius: '0.75rem',
          width: '100%',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          transform: isOpen ? 'scale(1.02)' : 'scale(1)',
          boxShadow: isOpen ? '0 8px 25px rgba(14, 165, 233, 0.2)' : 'none',
        }}
      >
        <FolderOpen 
          size={24} 
          style={{
            color: 'var(--accent-primary)',
            transform: isOpen ? 'rotate(15deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s ease',
          }}
        />
        <span style={{ 
          color: 'var(--text-primary)', 
          fontWeight: 500,
          fontSize: '1rem',
        }}>
          {label}
        </span>
      </button>
      
      {isOpen && (
        <div
          className="folder-content"
          style={{
            marginTop: '1rem',
            padding: '1.5rem',
            background: 'var(--bg-secondary)',
            border: '2px solid var(--accent-primary)',
            borderRadius: '0.75rem',
            animation: 'fadeIn 0.4s ease, folderOpen 0.5s ease',
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
};

// ============ SHINY TEXT BUTTON COMPONENT ============
export const ShinyButton = ({ 
  children, 
  onClick, 
  variant = 'primary',
  disabled = false,
  className = '' 
}) => {
  const getBackgroundStyle = () => {
    switch (variant) {
      case 'primary':
        return 'linear-gradient(135deg, var(--accent-primary), var(--medical-cyan))';
      case 'success':
        return 'linear-gradient(135deg, var(--success), #059669)';
      case 'danger':
        return 'linear-gradient(135deg, var(--danger), #dc2626)';
      case 'purple':
        return 'linear-gradient(135deg, var(--medical-purple), #7c3aed)';
      default:
        return 'linear-gradient(135deg, var(--accent-primary), var(--medical-cyan))';
    }
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`shiny-button ${className}`}
      style={{
        position: 'relative',
        overflow: 'hidden',
        padding: '0.75rem 1.5rem',
        border: 'none',
        borderRadius: '0.5rem',
        background: getBackgroundStyle(),
        color: 'white',
        fontWeight: 600,
        fontSize: '1rem',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s ease',
        opacity: disabled ? 0.5 : 1,
        boxShadow: '0 4px 15px rgba(14, 165, 233, 0.3)',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(14, 165, 233, 0.4)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 4px 15px rgba(14, 165, 233, 0.3)';
        }
      }}
    >
      <span style={{ position: 'relative', zIndex: 2 }}>{children}</span>
      <span
        className="shine-effect"
        style={{
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
          animation: 'shine 3s infinite',
          pointerEvents: 'none',
        }}
      />
    </button>
  );
};

// ============ FADE IN CONTAINER COMPONENT ============
export const FadeInContainer = ({ children, delay = 0, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timeout);
  }, [delay]);

  return (
    <div
      className={`fade-in-container ${className}`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
        transition: 'all 0.8s ease',
      }}
    >
      {children}
    </div>
  );
};

// ============ EXAMPLE USAGE IN StartSessionModal ============
// 
// import { AnimatedListItem, AnimatedFolderInput, ShinyButton } from '../animations/AnimatedComponents';
//
// const StartSessionModal = ({ onClose, onStart }) => {
//   const cases = [
//     { id: 1, title: 'Acute Chest Pain', difficulty: 'Moderate' },
//     { id: 2, title: 'Diabetic Emergency', difficulty: 'High' },
//     // ... more cases
//   ];
//
//   return (
//     <div className="modal-overlay">
//       <div className="modal">
//         <h2>Select a Case</h2>
//         <div className="cases-list">
//           {cases.map((caseItem, index) => (
//             <AnimatedListItem key={caseItem.id} delay={index * 100}>
//               <div className="case-card">
//                 <h3>{caseItem.title}</h3>
//                 <span>{caseItem.difficulty}</span>
//               </div>
//             </AnimatedListItem>
//           ))}
//         </div>
//         <ShinyButton onClick={onStart} variant="primary">
//           Start Session
//         </ShinyButton>
//       </div>
//     </div>
//   );
// };
//
// ============ EXAMPLE USAGE IN UploadDocumentModal ============
//
// const UploadDocumentModal = ({ onClose, onComplete }) => {
//   const [folderOpen, setFolderOpen] = useState(false);
//
//   return (
//     <div className="modal-overlay">
//       <div className="modal">
//         <h2>Upload Document</h2>
//         <AnimatedFolderInput
//           isOpen={folderOpen}
//           onToggle={() => setFolderOpen(!folderOpen)}
//           label="Choose File to Upload"
//         >
//           <input 
//             type="file" 
//             accept=".docx,.pdf"
//             className="file-input"
//           />
//         </AnimatedFolderInput>
//       </div>
//     </div>
//   );
// };