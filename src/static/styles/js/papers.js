var buttons = document.querySelectorAll(".paper_input")
console.log(buttons)
console.log(1600)

buttons.forEach((button) => {
    button.addEventListener('click', ChangeNameOnClick);
  });


function ChangeNameOnClick(el){
    console.log(el)
}