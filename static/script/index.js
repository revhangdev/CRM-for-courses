  function submitForm(id) {
        // Відправка обраного id на сервер
        var userTypeInput = document.createElement("input");
        userTypeInput.setAttribute("type", "hidden");
        userTypeInput.setAttribute("name", "userType");
        userTypeInput.setAttribute("value", id);
        if (id === 'adminLogin') {
            document.forms[0].appendChild(userTypeInput); // Використовуйте форму для адміна (forms[0])
        } else {
            document.forms[1].appendChild(userTypeInput); // Використовуйте форму для вчителя (forms[1])
        }
    }
