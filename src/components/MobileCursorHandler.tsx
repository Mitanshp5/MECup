import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const MobileCursorHandler = () => {
    const location = useLocation();

    useEffect(() => {
        // Check if we are on a mobile route but NOT the login page
        const isMobileRoute = location.pathname.startsWith("/mobile");
        const isLoginPage = location.pathname === "/mobile/login";

        if (isMobileRoute && !isLoginPage) {
            // Create and inject style tag
            const style = document.createElement('style');
            style.id = 'mobile-cursor-style';
            style.innerHTML = `
        * {
          cursor: none !important;
        }
        /* Restore cursor for inputs just in case, though touch doesn't usually need it */
        input, textarea {
          cursor: text !important;
        }
      `;
            document.head.appendChild(style);

            return () => {
                // Cleanup
                const existingStyle = document.getElementById('mobile-cursor-style');
                if (existingStyle) {
                    existingStyle.remove();
                }
            };
        } else {
            // Ensure cleanup if we navigate away
            const existingStyle = document.getElementById('mobile-cursor-style');
            if (existingStyle) {
                existingStyle.remove();
            }
        }
    }, [location.pathname]);

    return null;
};

export default MobileCursorHandler;
