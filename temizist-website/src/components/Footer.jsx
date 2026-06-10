import { Recycle, Github, Linkedin, Mail } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import './Footer.css';

const Footer = () => {
    const { t } = useLanguage();

    return (
        <footer className="footer">
            <div className="container">
                <div className="footer-content">
                    <div className="footer-brand">
                        <div className="brand-logo">
                            <Recycle size={32} color="#00D665" />
                            <span>TEMİZİST</span>
                        </div>
                        <p className="footer-tagline">{t('tagline')}</p>
                        <p className="footer-description">
                            {t('heroDescription')}
                        </p>
                    </div>

                    <div className="footer-section">
                        <h4 className="footer-title">{t('quickLinks')}</h4>
                        <ul className="footer-links">
                            <li><a href="#why-use">{t('whyTemizist')}</a></li>
                            <li><a href="#how-it-works">{t('howItWorks')}</a></li>
                        </ul>
                    </div>

                    <div className="footer-section">
                        <h4 className="footer-title">{t('team')}</h4>
                        <ul className="footer-links">
                            <li>Gökhan Acar</li>
                            <li>Mustafa Akgül</li>
                            <li>Gökdeniz Akbal</li>
                        </ul>
                    </div>

                    <div className="footer-section">
                        <h4 className="footer-title">{t('contact')}</h4>
                        <div className="social-links">
                            <a href="#" className="social-link" aria-label="GitHub">
                                <Github size={20} />
                            </a>
                            <a href="#" className="social-link" aria-label="LinkedIn">
                                <Linkedin size={20} />
                            </a>
                            <a href="#" className="social-link" aria-label="Email">
                                <Mail size={20} />
                            </a>
                        </div>
                    </div>
                </div>

                <div className="footer-bottom">
                    <p>&copy; 2025 TemizIST. {t('allRightsReserved')}</p>
                    <p className="footer-credit">
                        {t('graduationProject')}
                    </p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
