import { useHashRoute } from './hooks/useHashRoute';
import HomePage from './pages/HomePage';
import { PhasePage } from './pages/PhasePage';

export default function App() {
  const route = useHashRoute();

  if (route.type === 'phase') {
    return <PhasePage phaseId={route.phaseId} />;
  }

  return <HomePage scrollTo={route.section} />;
}
