var buttons = document.querySelectorAll(".paper_input")


buttons.forEach((button) => {
    button.addEventListener('click', ChangeNameOnClick);
  });


function ChangeNameOnClick(el){
    console.log(el)
}