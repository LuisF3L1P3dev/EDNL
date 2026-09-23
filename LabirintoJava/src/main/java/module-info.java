module br.edu.ifrn.labirintojava {
    requires javafx.controls;
    requires javafx.fxml;


    opens br.edu.ifrn.labirintojava.controller to javafx.fxml;
    exports br.edu.ifrn.labirintojava;
}
