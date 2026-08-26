import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BatchDetail } from "./pages/BatchDetail";
import { Batches } from "./pages/Batches";
import { Dashboard } from "./pages/Dashboard";
import { PaymentDetail } from "./pages/PaymentDetail";
import { Payments } from "./pages/Payments";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/batches" element={<Batches />} />
        <Route path="/batches/:batchId" element={<BatchDetail />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/payments/:paymentId" element={<PaymentDetail />} />
      </Routes>
    </Layout>
  );
}
