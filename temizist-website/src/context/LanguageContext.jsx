import { createContext, useContext, useState } from 'react';

const LanguageContext = createContext();

export const translations = {
    tr: {
        // Header
        home: 'Ana Sayfa',
        whyTemizist: 'Neden TemizIST?',
        howItWorks: 'Nasıl Çalışır?',
        downloadNow: 'Hemen İndir',

        // Hero
        tagline: 'Geleceği Geri Dönüştür',
        heroTitle: 'Atıklarınla',
        heroTitleGradient: 'Para Kazan!',
        heroDescription: 'Akıllı geri dönüşüm sistemiyle her atığınız için puan kazanın. Çevreyi koruyun, ödüller kazanın ve sürdürülebilir bir geleceğe katkıda bulunun.',
        howItWorksBtn: 'Nasıl Çalışır?',
        activeUsers: 'Aktif Kullanıcı',
        recycledWaste: 'Geri Dönüştürülen Atık',
        reducedCO2: 'Azaltılan CO₂',

        // Why Use
        whyUseTitle: 'Neden',
        whyUseDescription: 'Geri dönüşümü eğlenceli ve ödüllendirici hale getiren özellikler',
        earnMoney: 'Para Kazan',
        earnMoneyDesc: 'Her geri dönüşüm için puan kazanın ve bu puanları kampanyalarda kullanın. Çevreyi korurken cebiniz de dolsun!',
        protectEnvironment: 'Çevreyi Koru',
        protectEnvironmentDesc: 'Karbon ayak izinizi azaltın ve sürdürülebilir bir gelecek için katkıda bulunun. Her atık sayılır!',
        findNearby: 'Yakınını Bul',
        findNearbyDesc: 'Harita üzerinden en yakın akıllı geri dönüşüm kutularını kolayca keşfedin ve ulaşın.',
        trackProgress: 'İlerlemeni İzle',
        trackProgressDesc: 'Geri dönüşüm geçmişinizi görüntüleyin, istatistiklerinizi takip edin ve başarılarınızı kutlayın.',

        // How It Works
        howItWorksTitle: 'Nasıl',
        howItWorksTitle2: 'Çalışır?',
        howItWorksDescription: '5 basit adımda geri dönüşüme başlayın ve kazanmaya başlayın',
        step1Title: 'Uygulamayı İndir',
        step1Desc: 'App Store veya Google Play\'den TemizIST uygulamasını indirin ve hızlıca kayıt olun.',
        step2Title: 'QR Kodu Tara',
        step2Desc: 'En yakın akıllı geri dönüşüm kutusunu bulun ve üzerindeki QR kodu tarayın.',
        step3Title: 'Atığını At',
        step3Desc: 'Plastik veya kağıt atığınızı akıllı kutuya atın. Sistem otomatik olarak tanımlayacak.',
        step4Title: 'Puan Kazan',
        step4Desc: 'Her atık için otomatik olarak puan kazanın. Puanlarınız anında hesabınıza yüklenir.',
        step5Title: 'Ödüllerini Topla',
        step5Desc: 'Biriktirdiğiniz puanları kampanyalarda kullanın ve ödüllerinizi alın!',

        // Footer
        quickLinks: 'Hızlı Linkler',
        team: 'Ekip',
        contact: 'İletişim',
        allRightsReserved: 'Tüm hakları saklıdır.',
        graduationProject: 'Bilgisayar Mühendisliği Bitirme Projesi',
    },
    en: {
        // Header
        home: 'Home',
        whyTemizist: 'Why TemizIST?',
        howItWorks: 'How It Works?',
        downloadNow: 'Download Now',

        // Hero
        tagline: 'Recycle the Future',
        heroTitle: 'Earn Money with',
        heroTitleGradient: 'Your Waste!',
        heroDescription: 'Earn points for every recyclable item with our smart recycling system. Protect the environment, earn rewards, and contribute to a sustainable future.',
        howItWorksBtn: 'How It Works?',
        activeUsers: 'Active Users',
        recycledWaste: 'Recycled Waste',
        reducedCO2: 'Reduced CO₂',

        // Why Use
        whyUseTitle: 'Why',
        whyUseDescription: 'Features that make recycling fun and rewarding',
        earnMoney: 'Earn Money',
        earnMoneyDesc: 'Earn points for every recycling and use them in campaigns. Fill your wallet while protecting the environment!',
        protectEnvironment: 'Protect Environment',
        protectEnvironmentDesc: 'Reduce your carbon footprint and contribute to a sustainable future. Every waste counts!',
        findNearby: 'Find Nearby',
        findNearbyDesc: 'Easily discover and access the nearest smart recycling bins on the map.',
        trackProgress: 'Track Progress',
        trackProgressDesc: 'View your recycling history, track your statistics, and celebrate your achievements.',

        // How It Works
        howItWorksTitle: 'How It',
        howItWorksTitle2: 'Works?',
        howItWorksDescription: 'Start recycling and earning in 5 simple steps',
        step1Title: 'Download the App',
        step1Desc: 'Download TemizIST app from App Store or Google Play and register quickly.',
        step2Title: 'Scan QR Code',
        step2Desc: 'Find the nearest smart recycling bin and scan the QR code on it.',
        step3Title: 'Insert Your Waste',
        step3Desc: 'Insert your plastic or paper waste into the smart bin. The system will automatically identify it.',
        step4Title: 'Earn Points',
        step4Desc: 'Automatically earn points for each waste item. Your points are instantly added to your account.',
        step5Title: 'Collect Rewards',
        step5Desc: 'Use your accumulated points in campaigns and collect your rewards!',

        // Footer
        quickLinks: 'Quick Links',
        team: 'Team',
        contact: 'Contact',
        allRightsReserved: 'All rights reserved.',
        graduationProject: 'Computer Engineering Graduation Project',
    }
};

export const LanguageProvider = ({ children }) => {
    const [language, setLanguage] = useState('tr');

    const toggleLanguage = () => {
        setLanguage(prev => prev === 'tr' ? 'en' : 'tr');
    };

    const t = (key) => {
        return translations[language][key] || key;
    };

    return (
        <LanguageContext.Provider value={{ language, toggleLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
};
