function  deleteSure() {

    if (!confirm("Are you sure you want to delete?")) {
        console.log('hello')
        return false;
    }
}

function myFunction(x) {
    x.classList.toggle("fa-thumbs-down");
}

function uploadImage() {

    if(confirm("Are you sure you want to change Image?")) {
        document.getElementById("changeImage").submit();
    } else {
        return false
    }
}


let myCarousel = document.querySelector('#carouselSlider')
let carousel = new bootstrap.Carousel(myCarousel, {
    interval: 4000,
})
