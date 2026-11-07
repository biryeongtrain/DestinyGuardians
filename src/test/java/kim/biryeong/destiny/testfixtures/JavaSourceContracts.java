package kim.biryeong.destiny.testfixtures;

import com.sun.source.tree.*;
import com.sun.source.util.JavacTask;
import com.sun.source.util.TreeScanner;
import javax.tools.*;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/** JDK parser only: no compilation, annotation processing, class loading or extra dependency. */
public final class JavaSourceContracts {
    private JavaSourceContracts() {}
    public static ClassTree parse(String text) throws Exception {
        var compiler=ToolProvider.getSystemJavaCompiler();assertNotNull(compiler);
        var diagnostics=new DiagnosticCollector<JavaFileObject>();
        var input=new SimpleJavaFileObject(URI.create("string:///SourceContract.java"),JavaFileObject.Kind.SOURCE) {
            @Override public CharSequence getCharContent(boolean ignored) { return text; }
        };
        try(var files=compiler.getStandardFileManager(diagnostics,null,null)) {
            var task=(JavacTask)compiler.getTask(null,files,diagnostics,List.of("-proc:none"),null,List.of(input));
            var unit=task.parse().iterator().next();
            assertTrue(diagnostics.getDiagnostics().stream().noneMatch(d->d.getKind()==Diagnostic.Kind.ERROR),
                    ()->diagnostics.getDiagnostics().toString());
            return unit.getTypeDecls().stream().filter(ClassTree.class::isInstance).map(ClassTree.class::cast).findFirst().orElseThrow();
        }
    }
    public static <T extends Tree> List<T> nodes(Tree root,Class<T> type) {
        var result=new ArrayList<T>();
        new TreeScanner<Void,Void>() {
            @Override public Void scan(Tree tree,Void ignored) {
                if(type.isInstance(tree))result.add(type.cast(tree));
                return super.scan(tree,ignored);
            }
        }.scan(root,null);
        return List.copyOf(result);
    }
    public static String expression(String text) throws Exception {
        return nodes(parse("class Expected { Object value = "+text+"; }"),VariableTree.class)
                .getFirst().getInitializer().toString();
    }
}
