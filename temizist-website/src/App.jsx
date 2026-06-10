import Header from './components/Header';
import Hero from './components/Hero';
import WhyUse from './components/WhyUse';
import HowItWorks from './components/HowItWorks';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <div className="app">
      <Header />

      <main>
        <section id="hero">
          <Hero />
        </section>

        <section id="why-use">
          <WhyUse />
        </section>

        <section id="how-it-works">
          <HowItWorks />
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default App;
