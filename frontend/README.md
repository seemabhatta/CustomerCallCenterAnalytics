# Customer Call Center Analytics - Frontend

A modern React TypeScript frontend for the Customer Call Center Analytics system, providing a comprehensive interface for managing transcripts, analyses, plans, workflows, and executions.

## 🚀 Features

- **Linear Workflow Management**: Transcript → Analysis → Plan → Workflow → Execution
- **Real-time Dashboard**: KPIs, charts, and live event monitoring
- **Workflow Approval System**: Kanban-style board with approval/rejection workflows
- **Insights & Analytics**: Risk pattern analysis and compliance monitoring
- **Governance Simulator**: Policy configuration with real-time impact simulation
- **Responsive Design**: Works seamlessly across desktop and mobile devices

## 🛠️ Tech Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: Custom components following shadcn/ui patterns
- **State Management**: React Query (TanStack Query)
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios

## 📋 Prerequisites

- Node.js 18+ and npm/yarn
- Backend API server running on `http://localhost:8000`

## ⚙️ Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoint definitions
│   │   └── client.ts     # Axios setup and API functions
│   ├── components/       # Reusable UI components
│   │   └── ui/           # Base UI components (Button, Card, etc.)
│   ├── views/            # Main application views
│   │   ├── Dashboard.tsx
│   │   ├── TranscriptsView.tsx
│   │   ├── AnalysisView.tsx
│   │   ├── PlanView.tsx
│   │   ├── WorkflowView.tsx
│   │   ├── ExecutionView.tsx
│   │   ├── InsightsView.tsx
│   │   ├── RunsExplorer.tsx
│   │   └── GovernanceSimulator.tsx
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts      # API response types and interfaces
│   ├── utils/            # Utility functions
│   │   └── cn.ts         # Class name utility
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # React entry point
│   └── index.css         # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## 🔌 API Integration

The frontend connects to the backend API server and includes full integration with all available endpoints:

### Core Endpoints
- **Transcripts**: `/api/v1/transcripts` - CRUD operations for call transcripts
- **Analyses**: `/api/v1/analyses` - Risk analysis management
- **Plans**: `/api/v1/plans` - Action plan creation and approval
- **Workflows**: `/api/v1/workflows` - Workflow extraction and execution
- **Insights**: `/api/v1/insights` - Pattern discovery and recommendations

### Configuration
The API base URL is configured in `src/api/client.ts` and defaults to `http://localhost:8000`. Update this if your backend runs on a different port.

## 📱 Views Overview

### Dashboard
- Real-time KPIs and metrics
- Stage duration charts
- Risk distribution analytics
- Live event monitoring

### Transcripts
- List and search call transcripts
- Create new analyses from transcripts
- View transcript details and conversation flow

### Analysis
- View risk analysis results
- Risk categorization (High/Medium/Low)
- Trigger action plan creation

### Plans
- Manage action plans
- Plan approval workflow
- Extract workflows from plans

### Workflows
- Kanban-style approval board
- Approve/reject workflows
- Execute approved workflows
- Track execution history

### Execution
- Monitor job execution status
- View execution logs and details
- Track success/failure rates

### Insights
- Risk pattern discovery
- Compliance alerts
- Actionable recommendations
- Trend analysis

### Governance
- Policy configuration simulator
- Auto-approval rule management
- Impact analysis and projections

## 🎨 Styling

The application uses Tailwind CSS with a custom design system:

- **Colors**: Semantic color palette for status indicators
- **Components**: Consistent styling across all UI elements
- **Responsive**: Mobile-first design approach
- **Accessibility**: ARIA labels and keyboard navigation support

## 🔧 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Configuration

The application supports different environments (dev/staging/prod) which can be selected in the UI header dropdown.

### Adding New Views

1. Create a new component in `src/views/`
2. Add the view to the main navigation in `App.tsx`
3. Update the `TabValue` type in `src/types/index.ts`

### API Client Usage

```typescript
import { transcriptApi } from '@/api/client';

// Create a new transcript
const transcript = await transcriptApi.create({
  topic: 'payment_inquiry',
  customer_id: 'CUST_001'
});

// List all transcripts
const transcripts = await transcriptApi.list();
```

## 🚀 Deployment

### Production Build

```bash
npm run build
```

This creates an optimized build in the `dist/` directory.

### Environment Variables

Create a `.env` file for environment-specific configuration:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
```

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure the backend server is running on `http://localhost:8000`
   - Check CORS configuration in the backend

2. **Build Errors**
   - Clear node_modules and reinstall dependencies
   - Ensure Node.js version is 18+

3. **Styling Issues**
   - Rebuild Tailwind classes: `npm run build`
   - Check for conflicting CSS

## 🤝 Contributing

1. Follow the existing code structure and naming conventions
2. Add TypeScript types for new API endpoints
3. Include error handling in all API calls
4. Test components across different screen sizes
5. Update this README when adding new features

## 📄 License

This project is part of the Customer Call Center Analytics system.

---

For backend API documentation, see the main project README in the parent directory.