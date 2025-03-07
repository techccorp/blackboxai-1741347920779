// app/static/js/auth.js

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    const payrollIdInput = document.getElementById("payroll-id");
    const passwordInput = document.getElementById("password");
    const loginButton = document.getElementById("login-submit-btn");
    const loginErrors = document.getElementById("login-errors").querySelector("p");
    const loginErrorsContainer = document.getElementById("login-errors");
    
    const validateForm = () => {
      // Enhanced validation to match backend patterns
      const payrollIdValid = /^D[A-Z]-\d{6}$/.test(payrollIdInput.value.trim());
      const passwordValid = passwordInput.value.trim().length >= 8;
      
      loginButton.disabled = !(payrollIdValid && passwordValid);
      
      // Visual feedback
      payrollIdInput.classList.toggle('invalid', !payrollIdValid);
      passwordInput.classList.toggle('invalid', !passwordValid);
    };
  
    // Real-time validation
    payrollIdInput.addEventListener("input", () => {
      validateForm();
      // Auto-format payroll ID
      const val = payrollIdInput.value.trim().toUpperCase();
      if (/^D[A-Z]-\d{0,6}$/.test(val)) {
        payrollIdInput.value = val;
      }
    });
  
    passwordInput.addEventListener("input", validateForm);
  
    // Handle submit
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      loginErrorsContainer.classList.add("hidden");
      loginErrors.textContent = "";
  
      // Disable button during submission
      loginButton.disabled = true;
      const originalButtonText = loginButton.innerHTML;
      loginButton.innerHTML = '<div class="spinner"></div> Authenticating...';
  
      try {
        const response = await fetch("/api/auth/login", {  // Note API endpoint change
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
          },
          body: JSON.stringify({
            payroll_id: payrollIdInput.value.trim().toUpperCase(),  // Ensure uppercase
            password: passwordInput.value.trim()
          }),
        });
  
        const data = await response.json();
  
        if (!response.ok) {
          throw new Error(data.detail || "Login failed");
        }
  
        // Successful login handling
        if (data.user.requires_password_change) {
          window.location.href = `/auth/change-password?user=${data.user.id}`;
        } else {
          window.location.href = data.redirect_url || "/dashboard";
        }
        
      } catch (error) {
        loginErrorsContainer.classList.remove("hidden");
        loginErrors.textContent = error.message;
        console.error("Login error:", error);
      } finally {
        loginButton.disabled = false;
        loginButton.innerHTML = originalButtonText;
      }
    });
  
    // Add input masking for payroll ID
    payrollIdInput.addEventListener("keypress", (e) => {
      const key = e.key;
      const currentValue = payrollIdInput.value;
      
      // Allow: backspace, delete, tab, escape, enter
      if ([8, 9, 27, 13].includes(e.keyCode)) return;
      
      // Prevent invalid characters
      if (currentValue.length < 3) {
        if (!/[D]/.test(key)) e.preventDefault();
      } else if (currentValue.length === 1) {
        if (!/[A-Z]/.test(key)) e.preventDefault();
      } else if (currentValue.length === 2) {
        if (key !== "-") e.preventDefault();
      } else if (currentValue.length > 2 && currentValue.length < 9) {
        if (!/\d/.test(key)) e.preventDefault();
      } else {
        e.preventDefault();
      }
    });
  });
