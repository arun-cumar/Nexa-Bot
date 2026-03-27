
export const calculate = (num1, operator, num2) => {
    const n1 = parseFloat(num1);
    const n2 = parseFloat(num2);

    if (isNaN(n1) || isNaN(n2)) return "തെറ്റായ സംഖ്യകൾ!";

    switch (operator) {
        case '+': return n1 + n2;
        case '-': return n1 - n2;
        case '*': 
        case 'x': return n1 * n2;
        case '/': return n2 !== 0 ? n1 / n2 : "0 🤣!";
        default: return "error! (+, -, *, /)";
    }
};
