let questions = [
    "What is Python?",
    "Explain Django ORM.",
    "How do you handle team communication?"
];

let index = 0;

function submitAnswer() {
    let answer = document.getElementById("answer").value;

    if (!answer) {
        alert("Please enter an answer");
        return;
    }

    document.getElementById("answer").value = "";
    index++;

    if (index < questions.length) {
        document.getElementById("question").innerText = questions[index];
    } else {
        document.getElementById("question").innerText = "Interview Completed. Thank you!";
    }
}

document.getElementById("question").innerText = questions[0];
