import React from "react";

export const Card: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div className="rounded-lg shadow-md bg-white p-4">{children}</div>;
};

export const CardHeader: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return <div className="mb-2 font-bold text-lg">{children}</div>;
};

export const CardTitle: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return <h2 className="text-xl font-semibold">{children}</h2>;
};

export const CardContent: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return <div className="text-sm text-gray-600">{children}</div>;
};
