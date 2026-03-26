"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Line, Doughnut } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Filler,
  Tooltip,
  Legend,
);

// ─── Shared config ────────────────────────────────────────────────────────────

const CHART_DEFAULTS = {
  plugins: { legend: { display: false } },
  animation: { duration: 400 },
} as const;

export const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  to_be_reviewed: { label: "To Be Reviewed", color: "#9ca3af" },
  reviewed: { label: "Hold", color: "#3b82f6" },
  shortlisted: { label: "Shortlisted", color: "#059669" },
  rejected: { label: "Rejected", color: "#ef4444" },
};

export const CATEGORY_CONFIG: Record<
  string,
  { label: string; color: string; hover: string }
> = {
  excellent: { label: "Excellent", color: "#059669", hover: "#047857" },
  good: { label: "Good", color: "#3b82f6", hover: "#2563eb" },
  moderate: { label: "Moderate", color: "#f59e0b", hover: "#d97706" },
  bad: { label: "Bad", color: "#ef4444", hover: "#dc2626" },
};

export const SCORE_CATEGORY_COLORS: Record<string, string> = {
  excellent: "text-emerald-600",
  good: "text-blue-600",
  moderate: "text-amber-600",
  bad: "text-destructive",
};

// ─── StatusBreakdownChart ─────────────────────────────────────────────────────

interface StatusBreakdownChartProps {
  statusBreakdown: Record<string, number>;
}

export function StatusBreakdownChart({ statusBreakdown }: StatusBreakdownChartProps) {
  const chartData = {
    labels: Object.values(STATUS_LABELS).map((c) => c.label),
    datasets: [
      {
        data: Object.keys(STATUS_LABELS).map((k) => statusBreakdown[k] ?? 0),
        backgroundColor: Object.values(STATUS_LABELS).map((c) => c.color),
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  return (
    <div className="h-48">
      <Bar
        data={chartData}
        options={{
          ...CHART_DEFAULTS,
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { display: false }, ticks: { precision: 0 } },
            y: { grid: { display: false } },
          },
        }}
      />
    </div>
  );
}

// ─── CategoryDistributionChart ────────────────────────────────────────────────

interface CategoryDistributionChartProps {
  categoryDistribution: Record<string, number>;
}

export function CategoryDistributionChart({
  categoryDistribution,
}: CategoryDistributionChartProps) {
  const keys = Object.keys(CATEGORY_CONFIG);
  const chartData = {
    labels: keys.map((k) => CATEGORY_CONFIG[k].label),
    datasets: [
      {
        data: keys.map((k) => categoryDistribution[k] ?? 0),
        backgroundColor: keys.map((k) => CATEGORY_CONFIG[k].color),
        hoverBackgroundColor: keys.map((k) => CATEGORY_CONFIG[k].hover),
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  return (
    <div className="h-48">
      <Bar
        data={chartData}
        options={{
          ...CHART_DEFAULTS,
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { display: false } },
            y: { grid: { display: false }, ticks: { precision: 0 } },
          },
        }}
      />
    </div>
  );
}

// ─── ApplicationsOverTimeChart ────────────────────────────────────────────────

interface ApplicationsOverTimeChartProps {
  data: { date: string; count: number }[];
}

export function ApplicationsOverTimeChart({ data }: ApplicationsOverTimeChartProps) {
  const chartData = {
    labels: data.map((d) =>
      new Date(d.date).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
    ),
    datasets: [
      {
        data: data.map((d) => d.count),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59,130,246,0.12)",
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
      },
    ],
  };

  return (
    <div className="h-48">
      <Line
        data={chartData}
        options={{
          ...CHART_DEFAULTS,
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: { display: false },
              ticks: { maxTicksLimit: 8, maxRotation: 0 },
            },
            y: {
              grid: { color: "rgba(0,0,0,0.05)" },
              ticks: { precision: 0 },
              beginAtZero: true,
            },
          },
        }}
      />
    </div>
  );
}

// ─── JobProfileBarChart ───────────────────────────────────────────────────────

interface JobProfileBarChartProps {
  labels: string[];
  data: number[];
  height?: number;
}

export function JobProfileBarChart({ labels, data, height = 160 }: JobProfileBarChartProps) {
  const chartData = {
    labels,
    datasets: [
      {
        data,
        backgroundColor: "#3b82f6",
        hoverBackgroundColor: "#2563eb",
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  return (
    <div style={{ height }}>
      <Bar
        data={chartData}
        options={{
          ...CHART_DEFAULTS,
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { display: false }, ticks: { precision: 0 } },
            y: { grid: { display: false } },
          },
        }}
      />
    </div>
  );
}

// ─── DoughnutChart ────────────────────────────────────────────────────────────

const DOUGHNUT_COLORS = [
  "#8b5cf6",
  "#6366f1",
  "#3b82f6",
  "#06b6d4",
  "#10b981",
  "#f59e0b",
];

interface DoughnutChartProps {
  labels: string[];
  data: number[];
}

export function DoughnutChart({ labels, data }: DoughnutChartProps) {
  const chartData = {
    labels,
    datasets: [
      {
        data,
        backgroundColor: DOUGHNUT_COLORS,
        hoverOffset: 6,
      },
    ],
  };

  return (
    <div className="h-56 w-56">
      <Doughnut
        data={chartData}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 400 },
          plugins: {
            legend: {
              display: true,
              position: "bottom",
              labels: { boxWidth: 12, padding: 12 },
            },
          },
        }}
      />
    </div>
  );
}
