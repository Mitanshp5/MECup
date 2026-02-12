import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const MobileRedirect = ({ children }: { children: React.ReactNode }) => {
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const checkMobile = () => {
            // Check 1: Is screen width typical of mobile/tablet?
            const isSmallScreen = window.innerWidth < 1024; // iPad Pro is 1024, standard mobile < 768

            // Check 2: Are we on the network IP? (Strong indicator of mobile in this setup)
            const isNetworkAccess = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

            // Only redirect if we are at the root (dashboard) and not already in /mobile
            if ((isSmallScreen || isNetworkAccess) && !location.pathname.startsWith('/mobile')) {
                console.log("Mobile/Network device detected, redirecting to mobile dashboard");
                navigate('/mobile/login', { replace: true });
            }
        };

        checkMobile();
    }, [navigate, location]);

    return <>{children}</>;
};

export default MobileRedirect;
