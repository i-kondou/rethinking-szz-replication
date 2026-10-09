import java.lang.reflect.*;
import java.util.*;
import com.github.valfirst.jbehave.junit.monitoring.JUnitReportingRunner;
import org.jbehave.core.annotations.Given;
import org.jbehave.core.configuration.Configuration;
import org.jbehave.core.configuration.MostUsefulConfiguration;
import org.jbehave.core.embedder.Embedder;
import org.jbehave.core.io.LoadFromClasspath;
import org.jbehave.core.junit.JUnitStories;
import org.jbehave.core.model.Story;
import org.jbehave.core.reporters.NullStoryReporter;
import org.jbehave.core.reporters.StoryReporterBuilder;
import org.jbehave.core.steps.*;
import org.vividus.bdd.context.*;
import org.vividus.bdd.steps.*;
import org.vividus.bdd.variable.*;
import org.vividus.testcontext.SimpleTestContext;
import org.vividus.util.property.*;

/** Original classes; synthetic wiring, properties and story; no Spring or Allure. */
public class Probe {
    static Embedder embedder;
    static Configuration config;
    static InjectableStepsFactory factory;
    static BddRunContext context;
    static int beforeStory, conversions, stepExecutions;
    static String input;
    public static class Steps {
        @Given("value $value") public void value(String value) { stepExecutions++; }
    }
    public static class Fixture extends JUnitStories {
        public Fixture() {}
        @Override public Embedder configuredEmbedder() { return embedder; }
        @Override public Configuration configuration() { return config; }
        @Override public InjectableStepsFactory stepsFactory() { return factory; }
        @Override protected List<String> storyPaths() { return List.of("probe.story"); }
    }
    static Object proxy(Class<?> cls) {
        return Proxy.newProxyInstance(cls.getClassLoader(), new Class<?>[]{cls}, (p,m,a) -> {
            if (m.getName().equals("getPropertyValuesByFamily")) return Map.of("x", "hello");
            if (m.getReturnType()==Map.class) return Map.of();
            if (m.getName().equals("toString")) return "SyntheticPropertySource";
            throw new UnsupportedOperationException(m.toString());
        });
    }
    static void setter(Object object, String name, Object value) throws Exception {
        for (Method m: object.getClass().getMethods()) if(m.getName().equals(name)&&m.getParameterCount()==1) {
            m.invoke(object,value); return;
        }
        throw new NoSuchMethodException(name);
    }
    static void configure(String mode, boolean init) throws Exception {
        context = new BddRunContext();
        if(init) context.putRunningBatch("batch-1");
        IPropertyMapper mapper=(IPropertyMapper)proxy(IPropertyMapper.class);
        IPropertyParser parser=(IPropertyParser)proxy(IPropertyParser.class);
        VariablesFactory variables;
        try {
            variables=VariablesFactory.class.getConstructor(IPropertyParser.class,IPropertyMapper.class,IBddRunContext.class)
                .newInstance(parser,mapper,context);
        } catch(NoSuchMethodException oldFactory) {
            variables=VariablesFactory.class.getConstructor().newInstance();
            setter(variables,"setPropertyParser",parser);
        }
        variables.init();
        BddVariableContext vc = new BddVariableContext();
        vc.setTestContext(new SimpleTestContext());
        vc.setVariablesFactory(variables);
        ParameterAdaptor pa = new ParameterAdaptor();
        pa.setBddVariableContext(vc);
        ExpressionAdaptor ea = new ExpressionAdaptor();
        ea.setProcessors(List.of());
        config=new MostUsefulConfiguration();
        config.useParameterConverters(new ParameterConvertersDecorator(config,pa,ea) {
            @Override public Object convert(String v, Type t) {
                conversions++; System.out.println("CONVERT "+v+" to "+t);
                return super.convert(v,t);
            }
        });
        input=mode.equals("examples")
            ? "Scenario: example\nGiven value <v>\nExamples:\n|v|\n|${x}|\n"
            : mode.equals("parameter") ? "Scenario: parameter\nGiven value ${x}\n"
            : "Scenario: plain\nGiven value hello\n";
        config.useStoryLoader(new LoadFromClasspath() {
            @Override public String loadStoryAsText(String path) { return input; }
        });
        config.useStoryReporterBuilder(new StoryReporterBuilder().withReporters(new NullStoryReporter() {
            @Override public void beforeStory(Story s,boolean given) {
                beforeStory++; System.out.println("BEFORE_STORY "+s.getPath());
            }
        }));
        factory=new InstanceStepsFactory(config,new Steps());
        Class<?> ec=Class.forName("org.vividus.bdd.BatchedEmbedder");
        try {
            embedder=(Embedder)ec.getConstructor().newInstance();
            setter(embedder,"setBddRunContext",context);
            Object provider=Class.forName("org.vividus.bdd.EmbedderControlsProvider").getConstructor().newInstance();
            setter(provider,"setPropertyMapper",mapper);
            setter(provider,"setStoryExecutionTimeout","300");
            setter(provider,"setIgnoreFailureInStories",true);
            provider.getClass().getMethod("init").invoke(provider);
            setter(embedder,"setEmbedderControlsProvider",provider);
        } catch (NoSuchMethodException missingOldConstructor) {
            Class<?> storageClass=Class.forName("org.vividus.bdd.batch.BatchStorage");
            Object storage=storageClass.getConstructors()[0].newInstance(mapper,"300",List.of());
            Constructor<?> c=ec.getConstructors()[0];
            embedder=(Embedder)(c.getParameterCount()==2 ? c.newInstance(context,storage) : c.newInstance(context,vc,storage));
        }
        embedder.useConfiguration(config);
        embedder.useStepsFactory(factory);
        embedder.usePerformableTree((org.jbehave.core.embedder.PerformableTree)
            Class.forName("org.vividus.bdd.BatchedPerformableTree").getConstructor().newInstance());
    }
    public static void main(String[] args) throws Exception {
        configure(args[0],Boolean.parseBoolean(args[1]));
        System.out.println("INPUT "+input.replace("\n","\\n"));
        try {
            JUnitReportingRunner r=new JUnitReportingRunner(Fixture.class);
            System.out.println("DESCRIPTION_OK "+r.getDescription()+" tests="+r.testCount());
            if(args.length>2 && args[2].equals("execute-control")) {
                embedder.getClass().getMethod("runStoriesAsPaths",Map.class)
                    .invoke(embedder,Map.of("batch-1",List.of("probe.story")));
                System.out.println("EXECUTION_CONTROL_OK");
            }
        } catch(Throwable t) {
            System.out.println("DESCRIPTION_ERROR "+t.getClass().getName()+": "+t.getMessage());
            t.printStackTrace(System.out);
        } finally {
            System.out.println("COUNTS beforeStory="+beforeStory+" conversions="+conversions+" stepExecutions="+stepExecutions);
            if(embedder.hasExecutorService()) embedder.executorService().shutdownNow();
        }
    }
}
