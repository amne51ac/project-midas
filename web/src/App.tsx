import { useHashRoute } from './hooks/useHashRoute';
import { usePageMeta } from './hooks/usePageMeta';
import { getPageMeta } from './config/siteMeta';
import HomePage from './pages/HomePage';
import { PhasePage } from './pages/PhasePage';

export default function App() {
  const route = useHashRoute();
  usePageMeta(getPageMeta(route));

  if (route.type === 'phase') {
    return <PhasePage phaseId={route.phaseId} scrollTo={route.section} />;
  }

  return <HomePage scrollTo={route.section} />;
}
