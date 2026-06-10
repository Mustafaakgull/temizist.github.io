import { useState } from 'react';
import { Smartphone } from 'lucide-react';
import './Screenshots.css';

const Screenshots = () => {
    const [activeIndex, setActiveIndex] = useState(0);

    const screenshots = [
        {
            title: 'Hoş Geldiniz',
            description: 'Geleceği geri dönüştürün',
            image: '/screenshots/welcome.png'
        },
        {
            title: 'Ana Sayfa',
            description: 'Puanlarınızı ve istatistiklerinizi görün',
            image: '/screenshots/dashboard.png'
        },
        {
            title: 'Fırsatlar',
            description: 'Kampanyaları keşfedin',
            image: '/screenshots/opportunities.png'
        },
        {
            title: 'Geçmiş',
            description: 'Geri dönüşüm geçmişiniz',
            image: '/screenshots/history.png'
        },
        {
            title: 'QR Tarama',
            description: 'Atığınızı atın ve kazanın',
            image: '/screenshots/qr-scan.png'
        }
    ];

    return (
        <section className="section screenshots">
            <div className="container">
                <div className="section-header">
                    <h2 className="heading-2">
                        Uygulamayı <span className="text-gradient">Keşfedin</span>
                    </h2>
                    <p className="section-description">
                        Kullanıcı dostu arayüz ve akıllı özelliklerle dolu
                    </p>
                </div>

                <div className="screenshots-showcase">
                    <div className="screenshots-carousel">
                        {screenshots.map((screenshot, index) => (
                            <div
                                key={index}
                                className={`screenshot-item ${index === activeIndex ? 'active' : ''} ${index === activeIndex - 1 ? 'prev' : ''
                                    } ${index === activeIndex + 1 ? 'next' : ''}`}
                                onClick={() => setActiveIndex(index)}
                            >
                                <div className="phone-mockup-small">
                                    <div className="phone-frame-small glass">
                                        <Smartphone className="phone-placeholder" size={80} />
                                    </div>
                                </div>
                                <div className="screenshot-info">
                                    <h4>{screenshot.title}</h4>
                                    <p>{screenshot.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="carousel-dots">
                        {screenshots.map((_, index) => (
                            <button
                                key={index}
                                className={`dot ${index === activeIndex ? 'active' : ''}`}
                                onClick={() => setActiveIndex(index)}
                                aria-label={`Go to screenshot ${index + 1}`}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Screenshots;
