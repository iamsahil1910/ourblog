function  deleteSure() {

    if (!confirm("Are you sure you want to delete?")) {
        console.log('hello')
        return false;
    }
}