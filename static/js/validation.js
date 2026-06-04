document.addEventListener('DOMContentLoaded', () => {
    // Select forms
    const registerForm = document.getElementById('registerForm');
    const loginForm = document.getElementById('loginForm');

    // Regex Rules
    const rules = {
        full_name: {
            regex: /^[A-Za-z\s]{3,40}$/,
            errorMsg: 'Name must be 3-40 characters, letters only.'
        },
        phone: {
            regex: /^\d{10}$/,
            errorMsg: 'Phone must be exactly 10 digits.'
        },
        email: {
            regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            errorMsg: 'Please enter a valid email address.'
        },
        password: {
            // Min 8, Max 30, at least 1 upper, 1 lower, 1 number
            regex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,30}$/,
            errorMsg: '8-30 chars, uppercase, lowercase, and number required.'
        }
    };

    function validateInput(inputElement) {
        const fieldType = inputElement.name;
        if (!rules[fieldType]) return true; // Skip if no rule defined
        
        const value = inputElement.value.trim();
        const rule = rules[fieldType];
        
        // Error container
        let errorContainer = inputElement.nextElementSibling;
        if (!errorContainer || !errorContainer.classList.contains('invalid-feedback-custom')) {
            errorContainer = document.createElement('div');
            errorContainer.classList.add('invalid-feedback-custom');
            inputElement.parentNode.insertBefore(errorContainer, inputElement.nextSibling);
        }

        const isValid = rule.regex.test(value);
        
        if (value === '') {
            inputElement.classList.remove('is-valid', 'is-invalid');
            return false;
        }

        if (isValid) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
            errorContainer.textContent = rule.errorMsg;
        }
        
        return isValid;
    }

    function setupValidation(form) {
        if (!form) return;
        
        const inputs = form.querySelectorAll('.form-modern');
        const submitBtn = form.querySelector('button[type="submit"]');

        inputs.forEach(input => {
            input.addEventListener('input', () => {
                validateInput(input);
                checkFormValidity();
            });
        });

        function checkFormValidity() {
            let allValid = true;
            inputs.forEach(input => {
                const fieldType = input.name;
                if (rules[fieldType]) {
                    if (!rules[fieldType].regex.test(input.value.trim())) {
                        allValid = false;
                    }
                }
            });
            submitBtn.disabled = !allValid;
        }
        
        // Initial check in case of pre-filled data
        checkFormValidity();
    }

    setupValidation(registerForm);
    // Note: for login form, we might just want to check if they are not empty, 
    // but applying standard validation helps UX too.
    setupValidation(loginForm);
});
