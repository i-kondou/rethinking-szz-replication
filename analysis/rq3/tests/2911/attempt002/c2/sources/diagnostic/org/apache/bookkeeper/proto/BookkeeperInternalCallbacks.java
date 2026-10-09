package org.apache.bookkeeper.proto; public final class BookkeeperInternalCallbacks { public interface GenericCallback<T> { void operationComplete(int rc, T result); } }
