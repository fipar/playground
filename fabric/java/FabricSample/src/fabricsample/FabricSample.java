/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

package fabricsample;

//import com.mysql.fabric.jdbc.FabricMySQLDataSource;
import com.mysql.fabric.jdbc.FabricMySQLConnection;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;

/**
 *
 * @author fernandoipar
 */
public class FabricSample {
    
    private static final String url = "jdbc:mysql:fabric://192.168.70.100:8080/test?user=fabric&password=f4bric&fabricUsername=admin&fabricPassword=admin&fabricReportErrors=true";

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection(url);
        FabricMySQLConnection fabricCon = (FabricMySQLConnection) c;
        fabricCon.setServerGroupName("mycluster");
        ResultSet rs = fabricCon.createStatement().executeQuery("select @@version as version");
        rs.next();
        System.out.println(rs.getString("version"));
    }
    
}
