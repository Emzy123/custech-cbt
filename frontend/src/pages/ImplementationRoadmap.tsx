import React from 'react';
import Card from '../components/ui/Card';

const phases = [
  { id: 'R1', title: 'Foundation', items: ['RBAC users/roles', 'Academic sessions/semesters', 'Department/course APIs', 'Student CSV import'] },
  { id: 'R2', title: 'Question Workflow', items: ['Draft and submit', 'Approve/reject/request changes', 'Bulk question CSV import'] },
  { id: 'R3', title: 'Scheduling', items: ['Create exams', 'Blueprint validation', 'Venue allocation and seat numbering'] },
  { id: 'R4', title: 'Exam Runtime', items: ['Randomized attempt map', 'Autosave answers', 'Submission endpoint'] },
  { id: 'R5', title: 'Proctoring', items: ['Proctoring event ingestion', 'Invigilator interventions', 'Terminate action support'] },
  { id: 'R6', title: 'Results', items: ['Automated grading', 'Result release', 'Question exclusion and item analysis'] },
  { id: 'R7', title: 'Ops and Governance', items: ['Audit query APIs', 'Security alert APIs', 'Backup run APIs'] },
];

const ImplementationRoadmap: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-6xl mx-auto space-y-4">
        <h1 className="text-2xl font-bold">CUSTECH GST CBT Implementation Status</h1>
        <p className="text-slate-600">
          This dashboard reflects the delivered Django + React + PostgreSQL implementation tracks.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {phases.map((phase) => (
            <Card key={phase.id} className="p-4">
              <h2 className="font-semibold">{phase.id}: {phase.title}</h2>
              <ul className="list-disc ml-5 mt-2 text-sm text-slate-700">
                {phase.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ImplementationRoadmap;
