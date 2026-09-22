package br.edu.ifrn.labirintojava;

import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.stage.Stage;
import br.edu.ifrn.labirintojava.controller.MainController;

import java.io.IOException;

public class LabirintoApplication extends Application {
    @Override
    public void start(Stage stage) throws IOException {
        FXMLLoader fxmlLoader = new FXMLLoader(LabirintoApplication.class.getResource("/br/edu/ifrn/labirintojava/view/main.fxml"));
        Scene scene = new Scene(fxmlLoader.load(), 1250, 850);
        scene.getStylesheets().add(LabirintoApplication.class.getResource("/br/edu/ifrn/labirintojava/view/style.css").toExternalForm());
        MainController controller = fxmlLoader.getController();
        stage.setOnCloseRequest(event -> controller.shutdown());
        stage.setTitle("Labirinto: Busca Gulosa e A*");
        stage.setScene(scene);
        stage.show();
    }
}
