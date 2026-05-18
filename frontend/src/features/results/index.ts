export const resultEndpoints = {
  gradeAttempt: (attemptId: number) => `/api/v1/attempts/${attemptId}/grade`,
  release: (examId: number) => `/api/v1/exams/${examId}/results/release`,
  studentResult: (attemptId: number) => `/api/v1/attempts/${attemptId}/result`,
  review: (attemptId: number) => `/api/v1/attempts/${attemptId}/review`,
  exportCsv: (examId: number) => `/api/v1/exams/${examId}/results/export.csv`,
  exclude: (examId: number, questionId: number) =>
    `/api/v1/exams/${examId}/questions/${questionId}/exclude`,
  itemAnalysis: (examId: number) => `/api/v1/exams/${examId}/item-analysis`,
};
