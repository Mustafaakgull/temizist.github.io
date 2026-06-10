import { useState } from 'react';
import { Recycle, Menu, X, Languages } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import './Header.css';

const Header = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { language, toggleLanguage, t } = useLanguage();

    const scrollToSection = (sectionId) => {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
            setIsMenuOpen(false);
        }
    };

    return (
        <header className="header glass">
            <div className="container">
                <nav className="nav">
                    <div className="nav-brand">
                        <Recycle size={28} color="#00D665" />
                        <span className="brand-name">TEMİZİST</span>
                    </div>

                    <div className={`nav-menu ${isMenuOpen ? 'active' : ''}`}>
                        <button onClick={() => scrollToSection('hero')} className="nav-link">
                            {t('home')}
                        </button>
                        <button onClick={() => scrollToSection('why-use')} className="nav-link">
                            {t('whyTemizist')}
                        </button>
                        <button onClick={() => scrollToSection('how-it-works')} className="nav-link">
                            {t('howItWorks')}
                        </button>

                        <button onClick={toggleLanguage} className="language-toggle" aria-label="Change language">
                            <Languages size={18} />
                            <span>{language === 'tr' ? 'EN' : 'TR'}</span>
                        </button>

                        <button className="btn btn-primary btn-sm">
                            {t('downloadNow')}
                        </button>
                    </div>

                    <button
                        className="menu-toggle"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </nav>
            </div>
        </header>
    );
};

export default Header;
