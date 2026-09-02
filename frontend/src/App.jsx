import React, { useState } from 'react';
import './App.css';
import CaseList from './pages/CaseList';
import CaseDetail from './pages/CaseDetail';

export default function App() {
  const [currentPage, setCurrentPage] = useState('cases');
  const [selectedCase, setSelectedCase] = useState(null);

  const handleSelectCase = (caseData) => {
    setSelectedCase(caseData);
    setCurrentPage('detail');
  };

  const handleBackToCases = () => {
    setCurrentPage('cases');
    setSelectedCase(null);
  };

  return (
    <div className="app">
      {currentPage === 'cases' && (
        <CaseList 
          onSelectCase={handleSelectCase}
          onCreateCase={handleSelectCase}
        />
      )}
      {currentPage === 'detail' && selectedCase && (
        <CaseDetail 
          caseData={selectedCase}
          onBack={handleBackToCases}
        />
      )}
    </div>
  );
}
