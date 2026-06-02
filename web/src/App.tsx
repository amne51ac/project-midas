import { useAppRoute } from './routing/appRoute';
import { usePageMeta } from './hooks/usePageMeta';
import { getPageMeta } from './config/siteMeta';
import HomePage from './pages/HomePage';
import { PhasePage } from './pages/PhasePage';
import FindingsPage from './pages/FindingsPage';

export default function App() {
  const route = useAppRoute();
  usePageMeta(getPageMeta(route), route);

  if (route.type === 'findings') {
    return <FindingsPage />;
  }

  if (route.type === 'phase') {
    return <PhasePage phaseId={route.phaseId} scrollTo={route.section} />;
  }

  return <HomePage scrollTo={route.section} />;
}
