import { useAppRoute } from './routing/appRoute';
import { usePageMeta } from './hooks/usePageMeta';
import { getPageMeta } from './config/siteMeta';
import HomePage from './pages/HomePage';
import ContinuedPage from './pages/ContinuedPage';
import CredencePage from './pages/CredencePage';

export default function App() {
  const route = useAppRoute();
  usePageMeta(getPageMeta(route), route);

  if (route.type === 'continued') {
    return <ContinuedPage scrollTo={route.section} />;
  }

  if (route.type === 'credence') {
    return <CredencePage />;
  }

  return <HomePage scrollTo={route.section} />;
}
