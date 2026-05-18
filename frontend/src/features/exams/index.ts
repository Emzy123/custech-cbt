export const examEndpoints = {
  create: '/api/v1/exams',
  blueprintValidate: (examId: number) => `/api/v1/exams/${examId}/blueprint/validate`,
  allocateVenues: (examId: number) => `/api/v1/exams/${examId}/venues/allocate`,
  slipPdf: (seatId: number) => `/api/v1/exams/seats/${seatId}/slip.pdf`,
  startAttempt: (examId: number) => `/api/v1/exams/${examId}/attempts/start`,
  attemptAnswer: (attemptId: number) => `/api/v1/attempts/${attemptId}/answers`,
  attemptClock: (attemptId: number) => `/api/v1/attempts/${attemptId}/clock`,
  attemptSubmit: (attemptId: number) => `/api/v1/attempts/${attemptId}/submit`,
  attemptEvents: (attemptId: number) => `/api/v1/attempts/${attemptId}/events`,
};
